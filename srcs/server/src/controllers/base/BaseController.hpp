#pragma once

#include <drogon/HttpAppFramework.h>

namespace digiedu::controllers {
#define REGISTRATION_BEGIN                                                              \
static void registerController()                                                        \
{
#define PATH(method, path_pattern, ...)                                                 \
{                                                                                       \
constexpr const auto path = getRoutePath(path_pattern);                                 \
drogon::app().registerHandler(path.data(), &method, {__VA_ARGS__}, #method);            \
}
#define REGISTRATION_END                                                                \
}

    template <int N>
    struct string_literal {
        consteval string_literal(const char (&str)[N]) { // NOLINT(*-explicit-constructor)
            std::copy_n(str, N - 1, value);
        }

        [[nodiscard]] consteval static int size() {
            return N - 1;
        }

        char value[N - 1]{};
    };

    template <string_literal RoutePathPrefix>
    class BaseController {
    protected:
        template <int M>
        consteval static auto getRoutePath(const char (&suffix)[M]) {
            constexpr const auto N = RoutePathPrefix.size();
            std::array<char, N + M> result;
            std::copy_n(RoutePathPrefix.value, N, result.begin());
            std::copy_n(suffix, M, result.begin() + N);
            return result;
        }
    };
}
