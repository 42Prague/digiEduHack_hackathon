#pragma once

#include <drogon/HttpRequest.h>
#include "../../dependencies/libbcrypt2/include/bcrypt/BCrypt.hpp"

namespace digiedu::dao {
    struct User {
        Json::String id;
        Json::String name;
        Json::String surname;
        Json::String email;
        Json::String position;
        Json::String password, hashedPassword;
        Json::String accessLevel;

        static User fromCreateRequest(const drogon::HttpRequestPtr& request) {
            const auto& json = request->getJsonObject();
            return {
                "",
                (*json)["name"].asString(),
                (*json)["surname"].asString(),
                (*json)["email"].asString(),
                (*json)["position"].asString(),
                (*json)["password"].asString(),
                "",
                (*json)["access_level"].asString()
            };
        }

        static User fromLoginRequest(const drogon::HttpRequestPtr& request) {
            const auto& json = request->getJsonObject();
            return {
                "",
                "",
                "",
                (*json)["email"].asString(),
                "",
                (*json)["password"].asString()
            };
        }

        void hashPassword() {
            hashedPassword = BCrypt::generateHash(password);
        }

        bool checkPassword() const {
            return BCrypt::validatePassword(password, hashedPassword);
        }

        void execCreateSqlAsync(
            const drogon::orm::DbClientPtr& t,
            drogon::orm::ResultCallback resClb,
            drogon::orm::ExceptionCallback exClb
        ) const {
            t->execSqlAsync(
                "INSERT INTO user_account (id, name, surname, email, position, password_hash, access_level) VALUES"
                "(gen_random_uuid(), $1, $2, $3, $4, $5, $6)",
                std::move(resClb),
                std::move(exClb),
                name, surname, email, position, hashedPassword, accessLevel
            );
        }

        static void execGetAllSqlAsync(
            const drogon::orm::DbClientPtr& t,
            drogon::orm::ResultCallback resClb,
            drogon::orm::ExceptionCallback exClb
        ) {
            t->execSqlAsync(
                "SELECT id, name, surname, email, position, access_level FROM user_account",
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
                "SELECT id, name, surname, email, position, access_level FROM user_account WHERE id=$1",
                std::move(resClb),
                std::move(exClb),
                id
            );
        }

        static void execLoginSqlAsync(
            const drogon::orm::DbClientPtr& t,
            const std::string& email,
            drogon::orm::ResultCallback resClb,
            drogon::orm::ExceptionCallback exClb
        ) {
            t->execSqlAsync(
                "SELECT password_hash FROM user_account WHERE email=$1",
                std::move(resClb),
                std::move(exClb),
                email
            );
        }

        static Json::Value getRowToJson(const drogon::orm::Row& r) {
            Json::Value root(Json::objectValue);
            root["id"] = r["id"].as<std::string>();
            root["name"] = r["name"].as<std::string>();
            root["surname"] = r["surname"].as<std::string>();
            root["email"] = r["email"].as<std::string>();
            root["position"] = r["position"].as<std::string>();
            root["access_level"] = r["access_level"].as<std::string>();
            return root;
        }
    };
}
