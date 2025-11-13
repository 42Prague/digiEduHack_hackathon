add_executable(server)

target_link_libraries(server
    PRIVATE
    sqlpp11::sqlpp11
    sqlpp11::postgresql
    drogon
)

file(GLOB_RECURSE SOURCES *.cpp)
target_sources(server PRIVATE ${SOURCES})
