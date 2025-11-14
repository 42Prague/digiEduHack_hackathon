import { cleanEnv, str, url } from "envalid";

type Envs = {
  NODE_ENV: string;
  REG_FORM_URL: string;
};

export const envs: Envs = cleanEnv(process.env, {
  NODE_ENV: str({
    choices: ["development", "production"],
    default: "production",
  }),
  REG_FORM_URL: url({ default: "localhost:3100" }),
  //TLS: YES/NO? -> https/http, ws/wss
});
