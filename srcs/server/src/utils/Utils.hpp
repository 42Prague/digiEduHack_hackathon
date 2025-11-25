#pragma once

namespace digiedu::utils {
    static void emptyResponse(
        const std::function<void(const drogon::HttpResponsePtr&)>& callback,
        const drogon::HttpStatusCode code
    ) {
        callback(drogon::HttpResponse::newHttpResponse(code, drogon::CT_NONE));
    }

    static void jsonResponse(
        const std::function<void(const drogon::HttpResponsePtr&)>& callback,
        Json::Value&& json,
        const drogon::HttpStatusCode code
    ) {
        const auto res = drogon::HttpResponse::newHttpJsonResponse(std::move(json));
        res->setStatusCode(code);
        callback(res);
    }
}
