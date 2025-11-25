#pragma once

#include "base/BaseController.hpp"

namespace digiedu::controllers {
    class Schools : BaseController<"/schools"> {
    public:
        REGISTRATION_BEGIN
            PATH(Schools::create, "", drogon::Post)
            PATH(Schools::getAll, "", drogon::Get)
            PATH(Schools::get, "/{1}", drogon::Get)
        REGISTRATION_END
    private:
        static void create(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback);
        static void getAll(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback);
        static void get(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback, const std::string& schoolId);
    };
}
