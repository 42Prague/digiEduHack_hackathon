#pragma once

#include "base/BaseController.hpp"

namespace digiedu::controllers {
    class Users : BaseController<"/users"> {
    public:
        REGISTRATION_BEGIN
            PATH(Users::getAll, "", drogon::Get)
            PATH(Users::get, "/{name}", drogon::Get)
        REGISTRATION_END
    private:
        static void getAll(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback);
        static void get(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback, std::string&& userName);
    };
}
