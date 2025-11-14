#include "controllers/UserController.hpp"
#include "controllers/RegionController.hpp"

int main() {
  const char* hostPtr = std::getenv("SERVER_DB_HOST");
  const char* dbPtr = std::getenv("SERVER_DB_DB");
  const char* portPtr = std::getenv("SERVER_DB_PORT");
  const char* userPtr = std::getenv("SERVER_DB_USER");
  const char* passwordPtr = std::getenv("SERVER_DB_PASSWORD");
  const char* serverIpPtr = std::getenv("SERVER_IP");
  const char* serverPortPtr = std::getenv("SERVER_PORT");

  auto& app = drogon::app();

  // Logging
  app
      .addDbClient(drogon::orm::DbConfig(drogon::orm::PostgresConfig(
          hostPtr, std::stoi(portPtr), dbPtr,
          userPtr, passwordPtr, 1, "default",
          true, "", -1.0, false
      )))
      .setLogPath("", "", 100000000, 0, true)
      .setLogLevel(trantor::Logger::kTrace);

  // Configuration
  app.setThreadNum(0);

  // Register controllers
  LOG_TRACE << "--- CONTROLLERS REGISTRATION BEGIN ---";
  digiedu::controllers::Users::registerController();
  digiedu::controllers::Regions::registerController();
  LOG_TRACE << "--- CONTROLLERS REGISTRATION END ---";

  // Register listeners
  app.addListener(serverIpPtr,std::stoi(serverPortPtr));

  app.run();
  return 0;
}
