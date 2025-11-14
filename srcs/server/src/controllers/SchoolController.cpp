#include "SchoolController.hpp"
#include "../dao/School.hpp"
#include "../utils/Utils.hpp"

void digiedu::controllers::Schools::create(
    const drogon::HttpRequestPtr& request,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    auto school = dao::School::fromCreateRequest(request);
    drogon::app().getFastDbClient()->newTransactionAsync([s = std::move(school), c = std::move(callback)] (
        std::shared_ptr<drogon::orm::Transaction> t
    ) mutable {
        s.execCreateSqlAsync(
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

void digiedu::controllers::Schools::getAll(
    const drogon::HttpRequestPtr&,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    dao::School::execGetAllSqlAsync(
        drogon::app().getFastDbClient(),
        [callback] (const drogon::orm::Result& r) {
            Json::Value root(Json::arrayValue);
            for (size_t i = 0; i < r.size(); ++i)
                root.insert(i, dao::School::getRowToJson(r[i]));
            utils::jsonResponse(callback, std::move(root), drogon::k200OK);
        },
        [callback] (const drogon::orm::DrogonDbException& e) {
            utils::emptyResponse(callback, drogon::k500InternalServerError);
            std::cerr << e.base().what() << std::endl;
        }
    );
}

void digiedu::controllers::Schools::get(
    const drogon::HttpRequestPtr&,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback,
    const std::string& schoolId
) {
    dao::School::execGetSqlAsync(
        drogon::app().getFastDbClient(),
        schoolId,
        [callback] (const drogon::orm::Result& r) {
            if (r.empty()) {
                utils::emptyResponse(callback, drogon::k404NotFound);
                return;
            }
            utils::jsonResponse(callback, dao::School::getRowToJson(r[0]), drogon::k200OK);
        },
        [callback] (const drogon::orm::DrogonDbException& e) {
            utils::emptyResponse(callback, drogon::k500InternalServerError);
            std::cerr << e.base().what() << std::endl;
        }
    );
}
