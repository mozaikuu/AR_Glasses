#include <string>

#include <unity.h>

#include "text_protocol.h"

namespace {

using smart_glasses::fw::EscapeJson;
using smart_glasses::fw::ParseJsonStringField;
using smart_glasses::fw::UnescapeJson;

void test_escape_json_handles_special_chars() {
  const std::string input = "He said \"hi\"\\npath\\to\\tfile";
  const std::string expected = "He said \\\"hi\\\"\\\\npath\\\\to\\\\tfile";
  TEST_ASSERT_EQUAL_STRING(expected.c_str(), EscapeJson(input).c_str());
}

void test_unescape_json_handles_common_escapes() {
  const std::string input = "Line\\nTab\\tSlash\\/Quote\\\"";
  const std::string expected = "Line\nTab\tSlash/Quote\"";
  TEST_ASSERT_EQUAL_STRING(expected.c_str(), UnescapeJson(input).c_str());
}

void test_parse_json_string_field_reads_response_text() {
  const std::string json =
      "{\"response\":\"Hello\\\\nWorld\",\"tts_url\":\"http:\\\\/\\\\/x\\\\/y.wav\"}";
  const std::string expected = "Hello\nWorld";
  TEST_ASSERT_EQUAL_STRING(expected.c_str(), ParseJsonStringField(json, "response").c_str());
}

void test_parse_json_string_field_returns_empty_for_missing_key() {
  const std::string json = "{\"response\":\"ok\"}";
  TEST_ASSERT_EQUAL_STRING("", ParseJsonStringField(json, "missing").c_str());
}

void test_parse_json_string_field_unescapes_quotes() {
  const std::string json = "{\"response\":\"say \\\"hello\\\" now\"}";
  const std::string expected = "say \"hello\" now";
  TEST_ASSERT_EQUAL_STRING(expected.c_str(), ParseJsonStringField(json, "response").c_str());
}

}  // namespace

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_escape_json_handles_special_chars);
  RUN_TEST(test_unescape_json_handles_common_escapes);
  RUN_TEST(test_parse_json_string_field_reads_response_text);
  RUN_TEST(test_parse_json_string_field_returns_empty_for_missing_key);
  RUN_TEST(test_parse_json_string_field_unescapes_quotes);
  return UNITY_END();
}
