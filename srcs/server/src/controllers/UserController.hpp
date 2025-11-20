#pragma once

#include "base/BaseController.hpp"

namespace digiedu::controllers {
    class Users : BaseController<"/users"> {
    public:
        REGISTRATION_BEGIN
            PATH(Users::create, "", drogon::Post)
            PATH(Users::getAll, "", drogon::Get)
            PATH(Users::get, "/{1}", drogon::Get)
            PATH(Users::login, "/login", drogon::Post)
        REGISTRATION_END
    private:
        static void create(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback);
        static void getAll(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback);
        static void get(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback, const std::string& userId);
        static void login(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback);
    };
}
