import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";
import db from "../../db/knex";
import { config } from "../../config";
import { ApiError } from "../../middleware/errorHandler";
import type { RegisterInput, LoginInput, OAuthInput } from "./auth.schema";

const SALT_ROUNDS = 12;

function signToken(userId: string, email: string, subActive: boolean): { token: string; expiresIn: number } {
  const expiresIn = 86400; // 24h in seconds
  const token = jwt.sign(
    { sub: userId, email, sub_active: subActive, iat: Math.floor(Date.now() / 1000) },
    config.jwtSecret,
    { expiresIn }
  );
  return { token, expiresIn };
}

export async function register(input: RegisterInput) {
  const existing = await db("users").where({ email: input.email }).first();
  if (existing) throw new ApiError(409, "CONFLICT", "Email already registered");

  const passwordHash = await bcrypt.hash(input.password, SALT_ROUNDS);
  const [user] = await db("users").insert({ email: input.email, password_hash: passwordHash, name: input.name }).returning("*");

  await db("subscriptions").insert({ user_id: user.id, status: "inactive", plan: "free" });

  const { token, expiresIn } = signToken(user.id, user.email, false);
  return { userId: user.id, token, expiresIn };
}

export async function login(input: LoginInput) {
  const user = await db("users").where({ email: input.email }).first();
  if (!user) throw new ApiError(401, "UNAUTHORIZED", "Invalid email or password");
  if (!user.password_hash) throw new ApiError(401, "UNAUTHORIZED", "Account uses OAuth. Sign in with Google or Apple.");

  const valid = await bcrypt.compare(input.password, user.password_hash);
  if (!valid) throw new ApiError(401, "UNAUTHORIZED", "Invalid email or password");

  const sub = await db("subscriptions").where({ user_id: user.id }).first();
  const { token, expiresIn } = signToken(user.id, user.email, sub?.status === "active");
  return { userId: user.id, token, expiresIn };
}

export async function oauthLogin(input: OAuthInput) {
  // In production: verify idToken with Google/Apple. For now, trust the token's email claim.
  let email: string;
  let oauthId: string;

  try {
    // Google: decode without verification (production: use google-auth-library)
    if (input.provider === "google") {
      const decoded = JSON.parse(Buffer.from(input.idToken.split(".")[1], "base64").toString());
      email = decoded.email;
      oauthId = decoded.sub;
    } else {
      // Apple: similar — production: use apple-signin-auth
      const decoded = JSON.parse(Buffer.from(input.idToken.split(".")[1], "base64").toString());
      email = decoded.email || `${decoded.sub}@privaterelay.appleid.com`;
      oauthId = decoded.sub;
    }
  } catch {
    throw new ApiError(401, "UNAUTHORIZED", "Invalid OAuth token");
  }

  let user = await db("users").where({ oauth_provider: input.provider, oauth_id: oauthId }).first();
  let isNewUser = false;

  if (!user) {
    [user] = await db("users")
      .insert({ email, oauth_provider: input.provider, oauth_id: oauthId, name: email.split("@")[0] })
      .returning("*");
    await db("subscriptions").insert({ user_id: user.id, status: "inactive", plan: "free" });
    isNewUser = true;
  }

  const sub = await db("subscriptions").where({ user_id: user.id }).first();
  const { token, expiresIn } = signToken(user.id, user.email, sub?.status === "active");
  return { userId: user.id, token, expiresIn, isNewUser };
}
