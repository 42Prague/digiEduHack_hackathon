include(FetchContent)

FetchContent_Declare(sqlpp23
    GIT_REPOSITORY  https://github.com/rbock/sqlpp23
    GIT_TAG         origin/main
)

add_subdirectory(sqlpp23)
