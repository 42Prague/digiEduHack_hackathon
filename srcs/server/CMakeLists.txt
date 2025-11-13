cmake_minimum_required(VERSION 4.0)
project(server LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

### Dependencies ###
add_subdirectory(dependencies)

### Main Targets ###
add_subdirectory(src)
