add_executable(server)

target_link_libraries(server
    PRIVATE
    sqlpp11::sqlpp11
    # Corresponding targets for the connectors. These connectors need to be enabled in the the dependencies/sqlpp11 folder. These targets automatically link against sqlpp11::sqlpp11 and therefore sqlpp11::sqlpp11 doesn't need to be linked manually again
    # sqlpp11::sqlite3
    # sqlpp11::sqlcipher
    # sqlpp11::mysql
    # sqlpp11::mariadb
    sqlpp11::postgresql
)

target_sources(server PRIVATE main.cpp)
