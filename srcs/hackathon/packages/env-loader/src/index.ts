import { cleanEnv, str, port, url } from "envalid";

type Envs = {
  NODE_ENV: string;
  PORT: number;
  DATABASE_URL: string;
};

export const envs: Envs = cleanEnv(process.env, {
  NODE_ENV: str({
    choices: ["development", "production"],
    default: "production",
  }),
  PORT: port({ default: 3600 }),
  DATABASE_URL: url({ default: "localhost:5432" }),
});
