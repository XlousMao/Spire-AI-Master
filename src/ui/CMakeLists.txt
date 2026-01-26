cmake_minimum_required(VERSION 3.16)

project(SpireAIOverlay LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network)

qt_standard_project_setup()

add_executable(SpireAIOverlay
    main.cpp
)

target_link_libraries(SpireAIOverlay PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
)

if(WIN32)
    set_target_properties(SpireAIOverlay PROPERTIES WIN32_EXECUTABLE ON)
endif()
