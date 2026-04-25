#pragma once

#include <string>

namespace smart_glasses::fw {

std::string EscapeJson(const std::string& text);
std::string UnescapeJson(const std::string& text);
std::string ParseJsonStringField(const std::string& json, const std::string& key);

}  // namespace smart_glasses::fw
