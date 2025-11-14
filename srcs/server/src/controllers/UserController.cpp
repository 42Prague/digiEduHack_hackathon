#include "UserController.hpp"
#include "../dao/User.hpp"

void digiedu::controllers::Users::create(
    const drogon::HttpRequestPtr& request,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    auto user = dao::UserCreate::fromRequest(request);
    user.hashPassword();

    const auto dbClientPtr = drogon::app().getFastDbClient();
    dbClientPtr->newTransactionAsync([u = std::move(user), c1 = std::move(callback)] (std::shared_ptr<drogon::orm::Transaction> t) mutable {
        u.createSql(
            t,
            [t, c1] (const drogon::orm::Result&) {
                c1(drogon::HttpResponse::newHttpResponse(drogon::k200OK, drogon::CT_NONE));
            },
            [t, c1] (const drogon::orm::DrogonDbException& e) {
                c1(drogon::HttpResponse::newHttpResponse(drogon::k409Conflict, drogon::CT_NONE));
                t->rollback();
                std::cerr << e.base().what() << std::endl;
            }
        );
    });
}

void digiedu::controllers::Users::getAll(
    const drogon::HttpRequestPtr& request,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    // TODO
}

void digiedu::controllers::Users::get(
    const drogon::HttpRequestPtr& request,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback,
    const std::string& userId
) {
    // TODO
}
