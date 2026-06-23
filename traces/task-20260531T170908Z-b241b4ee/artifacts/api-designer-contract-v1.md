// ============================================================
// RoboEase Refactoring: API Contracts for Module Interfaces
// Language: TypeScript (detected from workspace)
// ============================================================

// ============================================================
// 1. Shared Utility Module (utils)
// ============================================================

export interface IUtils {
  /** Format a date string to 'YYYY-MM-DD' format. */
  formatDate(date: Date): string;

  /** Parse a date string in ISO format, returning null if invalid. */
  parseDate(dateStr: string): Date | null;

  /** Validate an email address format. Returns true if valid. */
  isValidEmail(email: string): boolean;

  /** Truncate a string to maxLength, appending '...' if truncated. */
  truncate(str: string, maxLength: number): string;

  /** Generate a unique identifier (UUID v4). */
  generateId(): string;
}

// ============================================================
// 2. Business Logic Module (services)
// ============================================================

export interface IUserService {
  /** Create a new user. Returns the created user. Throws on validation failure. */
  createUser(input: CreateUserInput): Promise<User>;

  /** Get user by ID. Returns null if not found. */
  getUserById(id: string): Promise<User | null>;

  /** List users with pagination. */
  listUsers(params: ListUsersParams): Promise<PaginatedResult<User>>;

  /** Update user fields. Returns the updated user. Throws if not found. */
  updateUser(id: string, input: UpdateUserInput): Promise<User>;

  /** Delete user by ID. Returns true if deleted, false if not found. */
  deleteUser(id: string): Promise<boolean>;
}

export interface IOrderService {
  /** Create a new order. Returns the created order. */
  createOrder(input: CreateOrderInput): Promise<Order>;

  /** Get order by ID. Returns null if not found. */
  getOrderById(id: string): Promise<Order | null>;

  /** List orders for a user with pagination. */
  listOrdersByUser(userId: string, params: ListOrdersParams): Promise<PaginatedResult<Order>>;

  /** Cancel an order. Throws if order cannot be cancelled. */
  cancelOrder(id: string): Promise<Order>;
}

// ============================================================
// 3. Data Access / Repository Module (repositories)
// ============================================================

export interface IUserRepository {
  /** Insert a new user. Returns the created user with generated ID. */
  insert(user: Omit<User, 'id' | 'createdAt'>): Promise<User>;

  /** Find user by ID. Returns null if not found. */
  findById(id: string): Promise<User | null>;

  /** Find user by email. Returns null if not found. */
  findByEmail(email: string): Promise<User | null>;

  /** List users with pagination and optional filters. */
  list(params: ListUsersParams): Promise<PaginatedResult<User>>;

  /** Update user fields. Returns the updated user. Throws if not found. */
  update(id: string, data: Partial<Omit<User, 'id' | 'createdAt'>>): Promise<User>;

  /** Delete user by ID. Returns true if deleted, false if not found. */
  delete(id: string): Promise<boolean>;
}

export interface IOrderRepository {
  /** Insert a new order. Returns the created order with generated ID. */
  insert(order: Omit<Order, 'id' | 'createdAt'>): Promise<Order>;

  /** Find order by ID. Returns null if not found. */
  findById(id: string): Promise<Order | null>;

  /** List orders for a user with pagination. */
  listByUser(userId: string, params: ListOrdersParams): Promise<PaginatedResult<Order>>;

  /** Update order status. Returns the updated order. Throws if not found. */
  updateStatus(id: string, status: OrderStatus): Promise<Order>;

  /** Delete order by ID. Returns true if deleted, false if not found. */
  delete(id: string): Promise<boolean>;
}

// ============================================================
// 4. Data Types (shared across modules)
// ============================================================

export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: Date;
}

export interface CreateUserInput {
  email: string;
  name: string;
}

export interface UpdateUserInput {
  email?: string;
  name?: string;
}

export interface Order {
  id: string;
  userId: string;
  productId: string;
  quantity: number;
  status: OrderStatus;
  createdAt: Date;
}

export type OrderStatus = 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';

export interface CreateOrderInput {
  userId: string;
  productId: string;
  quantity: number;
}

export interface ListUsersParams {
  page?: number;
  limit?: number;
  search?: string;
}

export interface ListOrdersParams {
  page?: number;
  limit?: number;
  status?: OrderStatus;
}

export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// ============================================================
// 5. Error Contract
// ============================================================

export class AppError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number = 500,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super('VALIDATION_ERROR', message, 400, details);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super('NOT_FOUND', `${resource} with id '${id}' not found`, 404);
    this.name = 'NotFoundError';
  }
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super('CONFLICT', message, 409);
    this.name = 'ConflictError';
  }
}

export class UnauthorizedError extends AppError {
  constructor(message: string = 'Unauthorized') {
    super('UNAUTHORIZED', message, 401);
    this.name = 'UnauthorizedError';
  }
}

// ============================================================
// 6. Usage Example
// ============================================================

// Example: Creating a user via service
// const userService: IUserService = new UserService(userRepository, utils);
// const user = await userService.createUser({ email: 'test@example.com', name: 'Test User' });
// console.log(user.id);

// Example: Listing users with pagination
// const result = await userService.listUsers({ page: 1, limit: 20 });
// console.log(result.data, result.totalPages);

// Example: Error handling
// try {
//   await userService.getUserById('nonexistent');
// } catch (error) {
//   if (error instanceof NotFoundError) {
//     console.error(error.message);
//   }
// }
