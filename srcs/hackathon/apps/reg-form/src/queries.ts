import { PrismaClient } from "../generated/client/client.js";

export type User = {
  email: string;
  firstName: string;
  lastName: string;
  password: string;
};

const prisma = new PrismaClient();

export async function findAllUsers() {
  const users = await prisma.user.findMany();
  return users;
}

export async function findUserById(id: number) {
  const user = await prisma.user.findUnique({ where: { id: id } });
  return user;
}

export async function updateUser(id: number, userData: object) {
  const user = await prisma.user.update({ where: { id: id }, data: userData });
  return user;
}

export async function deleteUser(id: number) {
  const user = await prisma.user.delete({ where: { id: id } });
  return user;
}
export async function createUser(user: User) {
  await prisma.user.create({
    data: {
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      password: user.password,
    },
  });
}
