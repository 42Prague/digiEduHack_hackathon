#include "UserController.hpp"
#include "../dao/User.hpp"
#include "../utils/Utils.hpp"

void digiedu::controllers::Users::create(
    const drogon::HttpRequestPtr& request,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    auto user = dao::User::fromCreateRequest(request);
    user.hashPassword();

    drogon::app().getFastDbClient()->newTransactionAsync([u = std::move(user), c = std::move(callback)] (
        std::shared_ptr<drogon::orm::Transaction> t
    ) mutable {
        u.execCreateSqlAsync(
            t,
            [t, c] (const drogon::orm::Result&) {
                utils::emptyResponse(c, drogon::k200OK);
            },
            [t, c] (const drogon::orm::DrogonDbException& e) {
                utils::emptyResponse(c, drogon::k500InternalServerError);
                t->rollback();
                std::cerr << e.base().what() << std::endl;
            }
        );
    });
}

void digiedu::controllers::Users::getAll(
    const drogon::HttpRequestPtr&,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    dao::User::execGetAllSqlAsync(
        drogon::app().getFastDbClient(),
        [callback] (const drogon::orm::Result& r) {
            Json::Value root(Json::arrayValue);
            for (size_t i = 0; i < r.size(); ++i)
                root.insert(i, dao::User::getRowToJson(r[i]));
            utils::jsonResponse(callback, std::move(root), drogon::k200OK);
        },
        [callback] (const drogon::orm::DrogonDbException& e) {
            utils::emptyResponse(callback, drogon::k500InternalServerError);
            std::cerr << e.base().what() << std::endl;
        }
    );
}

void digiedu::controllers::Users::get(
    const drogon::HttpRequestPtr&,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback,
    const std::string& userId
) {
    dao::User::execGetSqlAsync(
        drogon::app().getFastDbClient(),
        userId,
        [callback] (const drogon::orm::Result& r) {
            if (r.empty()) {
                utils::emptyResponse(callback, drogon::k404NotFound);
                return;
            }
            utils::jsonResponse(callback, dao::User::getRowToJson(r[0]), drogon::k200OK);
        },
        [callback] (const drogon::orm::DrogonDbException& e) {
            utils::emptyResponse(callback, drogon::k500InternalServerError);
            std::cerr << e.base().what() << std::endl;
        }
    );
}

void digiedu::controllers::Users::login(
    const drogon::HttpRequestPtr& request,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    auto user = dao::User::fromLoginRequest(request);
    dao::User::execLoginSqlAsync(
        drogon::app().getFastDbClient(),
        user.email,
        [callback, user] (const drogon::orm::Result& r) mutable {
            if (r.empty()) {
                utils::emptyResponse(callback, drogon::k404NotFound);
                return;
            }
            user.hashedPassword = r[0]["password_hash"].as<std::string>();
            utils::emptyResponse(callback, user.checkPassword() ? drogon::k200OK : drogon::k401Unauthorized);
        },
        [callback] (const drogon::orm::DrogonDbException& e) {
            utils::emptyResponse(callback, drogon::k500InternalServerError);
            std::cerr << e.base().what() << std::endl;
        }
    );
}
