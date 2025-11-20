#pragma once

#include <drogon/HttpRequest.h>

namespace digiedu::dao {
    struct Region {
        Json::String id;
        Json::String name;
        Json::String legalAddress;
        Json::String mainContact;

        static Region fromCreateRequest(const drogon::HttpRequestPtr& request) {
            const auto& json = request->getJsonObject();
            return {
                "",
                (*json)["name"].asString(),
                (*json)["legal_address"].asString(),
                (*json)["main_contact"].asString()
            };
        }

        void execCreateSqlAsync(
            const drogon::orm::DbClientPtr& t,
            drogon::orm::ResultCallback resClb,
            drogon::orm::ExceptionCallback exClb
        ) const {
            if (mainContact.empty()) {
                t->execSqlAsync(
                    "INSERT INTO region (id, name, legal_address) VALUES"
                    "(gen_random_uuid(), $1, $2)",
                    std::move(resClb),
                    std::move(exClb),
                    name, legalAddress
                );
            } else {
                t->execSqlAsync(
                    "INSERT INTO region (id, name, legal_address, main_contact) VALUES"
                    "(gen_random_uuid(), $1, $2, $3)",
                    std::move(resClb),
                    std::move(exClb),
                    name, legalAddress, mainContact
                );
            }
        }

        static void execGetAllSqlAsync(
            const drogon::orm::DbClientPtr& t,
            drogon::orm::ResultCallback resClb,
            drogon::orm::ExceptionCallback exClb
        ) {
            t->execSqlAsync(
                "SELECT * FROM region",
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
                "SELECT * FROM region WHERE id=$1",
                std::move(resClb),
                std::move(exClb),
                id
            );
        }

        static Json::Value getRowToJson(const drogon::orm::Row& r) {
            Json::Value root(Json::objectValue);
            root["id"] = r["id"].as<std::string>();
            root["name"] = r["name"].as<std::string>();
            root["legal_address"] = r["legal_address"].as<std::string>();
            root["main_contact"] = r["main_contact"].as<std::string>();
            return root;
        }
    };
}
