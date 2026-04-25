using NUnit.Framework;
using System;
using System.Reflection;
using UnityEngine;

namespace SmartGlasses.Tests.EditMode
{
  public class ApiEndpointResolverTests
  {
    private const string ResolverTypeName = "ApiEndpointResolver, Assembly-CSharp";

    private static Type ResolverType =>
      Type.GetType(ResolverTypeName) ?? throw new InvalidOperationException($"Type not found: {ResolverTypeName}");

    private static object? InvokeStatic(string methodName, params object[] args)
    {
      MethodInfo? method = ResolverType.GetMethod(methodName, BindingFlags.Public | BindingFlags.Static);
      Assert.IsNotNull(method, $"Expected method '{methodName}' on {ResolverTypeName}");
      return method!.Invoke(null, args);
    }

    private static string GetConstString(string fieldName)
    {
      FieldInfo? field = ResolverType.GetField(fieldName, BindingFlags.Public | BindingFlags.Static);
      Assert.IsNotNull(field, $"Expected field '{fieldName}' on {ResolverTypeName}");
      object? value = field!.GetValue(null);
      return value as string ?? string.Empty;
    }

    [SetUp]
    public void SetUp()
    {
      InvokeStatic("ClearOverride");
      InvokeStatic("ClearApiKeyOverride");
    }

    [TearDown]
    public void TearDown()
    {
      InvokeStatic("ClearOverride");
      InvokeStatic("ClearApiKeyOverride");
    }

    [Test]
    public void Resolve_UsesNormalizedFallback_WhenNoOverridesExist()
    {
      string resolved = (string)(InvokeStatic("Resolve", "https://api.example.com/") ?? string.Empty);
      Assert.AreEqual("https://api.example.com", resolved);
    }

    [Test]
    public void Resolve_UsesPlayerPrefsOverride_WhenPresent()
    {
      InvokeStatic("SetOverride", "http://10.0.0.2:8000/");

      string resolved = (string)(InvokeStatic("Resolve", "https://fallback.local/") ?? string.Empty);

      Assert.AreEqual("http://10.0.0.2:8000", resolved);
      Assert.AreEqual("http://10.0.0.2:8000", PlayerPrefs.GetString(GetConstString("PlayerPrefsKey")));
    }

    [Test]
    public void ResolveApiKey_UsesPlayerPrefsOverride_AndFallsBackAfterClear()
    {
      InvokeStatic("SetApiKeyOverride", "  test-key  ");
      Assert.AreEqual("test-key", (string)(InvokeStatic("ResolveApiKey", "fallback-key") ?? string.Empty));

      InvokeStatic("ClearApiKeyOverride");
      Assert.AreEqual("fallback-key", (string)(InvokeStatic("ResolveApiKey", "fallback-key") ?? string.Empty));
    }
  }
}
