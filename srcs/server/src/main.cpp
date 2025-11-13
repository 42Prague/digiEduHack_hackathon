#include <sqlpp11/postgresql/connection_config.h>
#include <sqlpp11/postgresql/connection_pool.h>

int main() {
  const char* hostPtr = std::getenv("SERVER_HOST");
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
  }

  return 0;
}
