#pragma once

#include "base/BaseController.hpp"

namespace digiedu::controllers {
    class Regions : BaseController<"/regions"> {
    public:
        REGISTRATION_BEGIN
            PATH(Regions::create, "", drogon::Post)
            PATH(Regions::getAll, "", drogon::Get)
            PATH(Regions::get, "/{1}", drogon::Get)
        REGISTRATION_END
    private:
        static void create(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback);
        static void getAll(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback);
        static void get(const drogon::HttpRequestPtr& request, std::function<void(const drogon::HttpResponsePtr&)>&& callback, const std::string& regionId);
    };
}
