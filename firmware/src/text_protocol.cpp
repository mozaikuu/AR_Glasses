#include "text_protocol.h"

namespace smart_glasses::fw {

std::string EscapeJson(const std::string& text) {
  std::string out;
  out.reserve(text.size() + 16);
  for (char c : text) {
    if (c == '\\' || c == '"') {
      out.push_back('\\');
      out.push_back(c);
    } else if (c == '\n') {
      out += "\\n";
    } else if (c == '\r') {
      out += "\\r";
    } else if (c == '\t') {
      out += "\\t";
    } else {
      out.push_back(c);
    }
  }
  return out;
}

std::string UnescapeJson(const std::string& text) {
  std::string out;
  out.reserve(text.size());
  for (size_t i = 0; i < text.size(); ++i) {
    char c = text[i];
    if (c == '\\' && i + 1 < text.size()) {
      char n = text[i + 1];
      if (n == 'n') {
        out.push_back('\n');
        ++i;
      } else if (n == 'r') {
        out.push_back('\r');
        ++i;
      } else if (n == 't') {
        out.push_back('\t');
        ++i;
      } else if (n == '"' || n == '\\' || n == '/') {
        out.push_back(n);
        ++i;
      } else {
        out.push_back(c);
      }
    } else {
      out.push_back(c);
    }
  }
  return out;
}

std::string ParseJsonStringField(const std::string& json, const std::string& key) {
  const std::string needle = "\"" + key + "\"";
  const size_t key_pos = json.find(needle);
  if (key_pos == std::string::npos) {
    return {};
  }

  const size_t colon_pos = json.find(':', key_pos + needle.size());
  if (colon_pos == std::string::npos) {
    return {};
  }

  const size_t quote_start = json.find('"', colon_pos + 1);
  if (quote_start == std::string::npos) {
    return {};
  }

  std::string value;
  bool escaped = false;
  for (size_t i = quote_start + 1; i < json.size(); ++i) {
    char c = json[i];
    if (!escaped && c == '\\') {
      escaped = true;
      value.push_back(c);
      continue;
    }
    if (!escaped && c == '"') {
      return UnescapeJson(value);
    }
    escaped = false;
    value.push_back(c);
  }

  return {};
}

}  // namespace smart_glasses::fw
