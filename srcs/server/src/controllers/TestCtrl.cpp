#include "TestCtrl.hpp"

void digiedu::controllers::Users::getAll(
    const drogon::HttpRequestPtr& /*request*/, std::function<void(const drogon::HttpResponsePtr&)> &&callback
) {
    auto resp = drogon::HttpResponse::newHttpResponse();
    resp->setStatusCode(drogon::k200OK);
    resp->setContentTypeCode(drogon::ContentType::CT_TEXT_HTML);
    resp->setBody("All!!!");
    callback(resp);
}

void digiedu::controllers::Users::get(
    const drogon::HttpRequestPtr& /*request*/, std::function<void(const drogon::HttpResponsePtr&)> &&callback,
    std::string&& userName
) {
    auto resp = drogon::HttpResponse::newHttpResponse();
    resp->setBody("Get: " + std::string(userName));
    callback(resp);
}
