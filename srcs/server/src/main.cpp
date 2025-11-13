#include <sqlpp11/postgresql/connection_config.h>
#include <sqlpp11/postgresql/connection_pool.h>
#include "controllers/TestCtrl.hpp"

int main() {
  /*const char* hostPtr = std::getenv("SERVER_HOST");
  const char* dbPtr = std::getenv("SERVER_DB");
  const char* portPtr = std::getenv("SERVER_PORT");
  const char* userPtr = std::getenv("SERVER_USER");
  const char* passwordPtr = std::getenv("SERVER_PASSWORD");

  auto config = std::make_shared<sqlpp::postgresql::connection_config>();
  config->host = hostPtr;
  config->port = std::stoi(std::string(portPtr));
  config->dbname = dbPtr;
  config->user = userPtr;
  config->password = passwordPtr;
  config->debug = true;
  auto pool = sqlpp::postgresql::connection_pool{config, 2};

  while (true) {
    try {
      pool.get();
    }
    catch (const std::exception& e) {
      std::cout << e.what() << std::endl;
      continue;
    }
    break;
  }

  {
    auto db = pool.get();
    int kek = 0;
    ++kek;
  }*/

  const char* serverIpPtr = std::getenv("SERVER_IP");

  auto& app = drogon::app();

  // Logging
  app
      .setLogPath("", "", 100000000, 0, true)
      .setLogLevel(trantor::Logger::kTrace);

  // Configuration
  app.setThreadNum(0);

  // Register controllers
  LOG_TRACE << "--- CONTROLLERS REGISTRATION BEGIN ---";
  digiedu::controllers::Users::registerController();
  LOG_TRACE << "--- CONTROLLERS REGISTRATION END ---";

  // Register listeners
  app.addListener(serverIpPtr,8080);

  app.run();
  return 0;
}
