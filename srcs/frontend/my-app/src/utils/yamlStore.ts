import yaml from "js-yaml";

const USERS_KEY = "user-store-yaml";

export type UserRole = "uploader" | "analyst";

export interface StoredUser {
  username: string;
  password: string;
  role: UserRole;
}

interface UserStore {
  users: StoredUser[];
}

function getDefaultStore(): UserStore {
  return { users: [] };
}

export function loadUserStore(): UserStore {
  const raw = localStorage.getItem(USERS_KEY);
  if (!raw) return getDefaultStore();

  try {
    const doc = yaml.load(raw) as unknown;
    if (
      typeof doc === "object" &&
      doc !== null &&
      Array.isArray((doc as any).users)
    ) {
      return doc as UserStore;
    }
    return getDefaultStore();
  } catch {
    return getDefaultStore();
  }
}

export function saveUserStore(store: UserStore): void {
  const yamlText = yaml.dump(store);
  localStorage.setItem(USERS_KEY, yamlText);
}

export function addUser(user: StoredUser): void {
  const store = loadUserStore();
  const exists = store.users.some((u) => u.username === user.username);
  if (exists) {
    throw new Error("User already exists");
  }
  store.users.push(user);
  saveUserStore(store);
}

export function findUser(username: string): StoredUser | undefined {
  const store = loadUserStore();
  return store.users.find((u) => u.username === username);
}
