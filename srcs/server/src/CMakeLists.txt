add_executable(server)

target_link_libraries(server
    PRIVATE 
    sqlpp23::sqlpp23
    # Corresponding targets for the connectors. These connectors need to be enabled in the the dependencies/sqlpp23 folder. These targets automatically link against sqlpp23::sqlpp23 and therefore sqlpp23::sqlpp23 doesn't need to be linked manually again
    # sqlpp23::sqlite3
    # sqlpp23::sqlcipher
    # sqlpp23::mysql
    # sqlpp23::mariadb
    sqlpp23::postgresql
)

target_sources(server PRIVATE main.cpp)
