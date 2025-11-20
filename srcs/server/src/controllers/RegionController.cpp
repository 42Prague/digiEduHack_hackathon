#include "RegionController.hpp"
#include "../dao/Region.hpp"
#include "../utils/Utils.hpp"

void digiedu::controllers::Regions::create(
    const drogon::HttpRequestPtr& request,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    auto region = dao::Region::fromCreateRequest(request);
    drogon::app().getFastDbClient()->newTransactionAsync([r = std::move(region), c = std::move(callback)] (
        std::shared_ptr<drogon::orm::Transaction> t
    ) mutable {
        r.execCreateSqlAsync(
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

void digiedu::controllers::Regions::getAll(
    const drogon::HttpRequestPtr&,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback
) {
    dao::Region::execGetAllSqlAsync(
        drogon::app().getFastDbClient(),
        [callback] (const drogon::orm::Result& r) {
            Json::Value root(Json::arrayValue);
            for (size_t i = 0; i < r.size(); ++i)
                root.insert(i, dao::Region::getRowToJson(r[i]));
            utils::jsonResponse(callback, std::move(root), drogon::k200OK);
        },
        [callback] (const drogon::orm::DrogonDbException& e) {
            utils::emptyResponse(callback, drogon::k500InternalServerError);
            std::cerr << e.base().what() << std::endl;
        }
    );
}

void digiedu::controllers::Regions::get(
    const drogon::HttpRequestPtr&,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback,
    const std::string& regionId
) {
    dao::Region::execGetSqlAsync(
        drogon::app().getFastDbClient(),
        regionId,
        [callback] (const drogon::orm::Result& r) {
            if (r.empty()) {
                utils::emptyResponse(callback, drogon::k404NotFound);
                return;
            }
            utils::jsonResponse(callback, dao::Region::getRowToJson(r[0]), drogon::k200OK);
        },
        [callback] (const drogon::orm::DrogonDbException& e) {
            utils::emptyResponse(callback, drogon::k500InternalServerError);
            std::cerr << e.base().what() << std::endl;
        }
    );
}
