import fastify from 'fastify';
import { runDocumentProcessing } from "../ingestionEngine/ingestionPipeline.js";

// ------------------------------------------------------------------
// 2. THE FASTIFY SERVER
// ------------------------------------------------------------------

const app = fastify({ logger: true });
const port = 5678;

app.get('/start-processing', async (request, reply) => {

  // 1. Log that we are triggering the function
  app.log.info('Triggering background processing...');

  // 2. Call the function WITHOUT 'await'
  // This is the "fire and forget" part.
  // We attach .catch() to log any errors and prevent an unhandled promise rejection.
  runDocumentProcessing().catch(err => {
    app.log.error(err, 'Background processing failed:');
  });

  // 3. Immediately send the response to the user
  reply.send({
    extraction: "started",
    time: new Date().toISOString()
  });
});

/**
 * Starts the server
 */
const start = async () => {
  try {
    await app.listen({ port: port, host: '0.0.0.0' });
    console.log(`Server listening on http://localhost:${port}`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
};

await start();