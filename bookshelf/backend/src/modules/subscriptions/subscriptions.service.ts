import db from "../../db/knex";
import { config } from "../../config";
import { ApiError } from "../../middleware/errorHandler";
import type { VerifyReceiptInput } from "./subscriptions.schema";

export async function getSubscriptionStatus(userId: string) {
  const sub = await db("subscriptions").where({ user_id: userId }).first();
  if (!sub) {
    await db("subscriptions").insert({ user_id: userId, status: "inactive", plan: "free" });
    return { active: false, plan: "free", expiresAt: undefined, willRenew: false };
  }

  return {
    active: sub.status === "active",
    plan: sub.plan,
    expiresAt: sub.expires_at,
    willRenew: sub.will_renew,
  };
}

export async function verifyReceipt(userId: string, input: VerifyReceiptInput) {
  if (!config.appStore.sharedSecret) {
    // Dev mode: accept any receipt
    await db("subscriptions")
      .where({ user_id: userId })
      .update({
        status: "active",
        plan: "premium",
        latest_receipt: input.receiptData,
        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        will_renew: true,
        updated_at: db.fn.now(),
      });

    return { valid: true, expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() };
  }

  // Production: verify with Apple
  const verifyUrl = config.appStore.environment === "production"
    ? "https://buy.itunes.apple.com/verifyReceipt"
    : "https://sandbox.itunes.apple.com/verifyReceipt";

  const response = await fetch(verifyUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      "receipt-data": input.receiptData,
      "password": config.appStore.sharedSecret,
      "exclude-old-transactions": true,
    }),
  });

  const result = await response.json() as any;

  if (result.status !== 0) {
    // If sandbox receipt sent to production, retry with sandbox
    if (result.status === 21007) {
      const sandboxRes = await fetch("https://sandbox.itunes.apple.com/verifyReceipt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ "receipt-data": input.receiptData, "password": config.appStore.sharedSecret }),
      });
      const sandboxResult = await sandboxRes.json() as any;
      if (sandboxResult.status !== 0) {
        throw new ApiError(400, "VALIDATION_ERROR", "Invalid receipt");
      }
      return processVerifiedReceipt(userId, sandboxResult);
    }
    throw new ApiError(400, "VALIDATION_ERROR", "Invalid receipt");
  }

  return processVerifiedReceipt(userId, result);
}

async function processVerifiedReceipt(userId: string, result: any) {
  const latestReceipt = result.latest_receipt_info?.[0];
  if (!latestReceipt) throw new ApiError(400, "VALIDATION_ERROR", "No subscription found in receipt");

  const expiresAt = new Date(parseInt(latestReceipt.expires_date_ms)).toISOString();
  const isActive = new Date(parseInt(latestReceipt.expires_date_ms)) > new Date();

  await db("subscriptions")
    .where({ user_id: userId })
    .update({
      status: isActive ? "active" : "expired",
      plan: "premium",
      original_transaction_id: latestReceipt.original_transaction_id,
      latest_receipt: result.latest_receipt,
      expires_at: expiresAt,
      will_renew: latestReceipt.auto_renew_status === "1",
      updated_at: db.fn.now(),
    });

  return { valid: true, expiresAt };
}
