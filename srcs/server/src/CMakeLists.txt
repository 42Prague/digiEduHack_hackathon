add_executable(server)

target_link_libraries(server
    PRIVATE
    drogon
    bcrypt
)

file(GLOB_RECURSE SOURCES *.cpp)
target_sources(server PRIVATE ${SOURCES})
