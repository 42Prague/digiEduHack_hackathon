#pragma once

#include <drogon/HttpRequest.h>

namespace digiedu::dao {
    struct School {
        Json::String id;
        Json::String name;
        Json::String legalId;
        Json::String address;
        Json::String mainContact;
        Json::String region;

        static School fromCreateRequest(const drogon::HttpRequestPtr& request) {
            const auto& json = request->getJsonObject();
            return {
                "",
                (*json)["name"].asString(),
                (*json)["legal_id"].asString(),
                (*json)["address"].asString(),
                (*json)["main_contact"].asString(),
                (*json)["region"].asString()
            };
        }

        void execCreateSqlAsync(
            const drogon::orm::DbClientPtr& t,
            drogon::orm::ResultCallback resClb,
            drogon::orm::ExceptionCallback exClb
        ) const {
            t->execSqlAsync(
                "INSERT INTO school (id, name, legal_id, address, main_contact, region) VALUES"
                "(gen_random_uuid(), $1, $2, $3, $4, $5)",
                std::move(resClb),
                std::move(exClb),
                name, legalId, address, mainContact, region
            );
        }

        static void execGetAllSqlAsync(
            const drogon::orm::DbClientPtr& t,
            drogon::orm::ResultCallback resClb,
            drogon::orm::ExceptionCallback exClb
        ) {
            t->execSqlAsync(
                "SELECT * FROM school",
                std::move(resClb),
                std::move(exClb)
            );
        }

        static void execGetSqlAsync(
            const drogon::orm::DbClientPtr& t,
            const std::string& id,
            drogon::orm::ResultCallback resClb,
            drogon::orm::ExceptionCallback exClb
        ) {
            t->execSqlAsync(
                "SELECT * FROM school WHERE id=$1",
                std::move(resClb),
                std::move(exClb),
                id
            );
        }

        static Json::Value getRowToJson(const drogon::orm::Row& r) {
            Json::Value root(Json::objectValue);
            root["id"] = r["id"].as<std::string>();
            root["name"] = r["name"].as<std::string>();
            root["legal_id"] = r["legal_id"].as<std::string>();
            root["address"] = r["address"].as<std::string>();
            root["main_contact"] = r["main_contact"].as<std::string>();
            root["region"] = r["region"].as<std::string>();
            return root;
        }
    };
}
