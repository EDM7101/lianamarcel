cmake_minimum_required(VERSION 3.18)
project(puzzle_lottery_vanity LANGUAGES CXX)

set(VANITY_DIR "${CMAKE_SOURCE_DIR}/third_party/VanitySearch")
set(CUDA_ROOT "/usr/local/cuda" CACHE PATH "CUDA Toolkit root")
set(GPU_CCAP "86" CACHE STRING "CUDA compute capability without dot, e.g. 86 for 8.6")

add_custom_target(
  vanitysearch ALL
  COMMAND ${CMAKE_MAKE_PROGRAM} -C ${VANITY_DIR} clean
  COMMAND ${CMAKE_MAKE_PROGRAM} -C ${VANITY_DIR} -j$ENV{CMAKE_BUILD_PARALLEL_LEVEL} gpu=1 CCAP=${GPU_CCAP} CUDA=${CUDA_ROOT}
  COMMENT "Building VanitySearch via upstream Makefile"
)
