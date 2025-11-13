import Fastify from "fastify";
import { envs } from "@repo/env-loader";
import { userRouter } from "./userRoutes.js";

const fastify = Fastify({ logger: true });
// global 404 handler - can be made custom per scope/context
fastify.setNotFoundHandler(function custom404(request, reply) {
  const payload = {
    message: "URL not found",
  };
  reply.send(payload);
});

fastify.register(userRouter, { prefix: "v1" });
fastify.register(userRouter, { prefix: "v2" });

fastify.listen({ host: "0.0.0.0", port: envs.PORT }, function (err) {
  if (err) {
    fastify.log.error(err);
    process.exit(1);
  }
});
