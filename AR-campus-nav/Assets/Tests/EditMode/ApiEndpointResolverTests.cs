using NUnit.Framework;
using UnityEngine;

namespace SmartGlasses.Tests.EditMode
{
  public class ApiEndpointResolverTests
  {
    [SetUp]
    public void SetUp()
    {
      ApiEndpointResolver.ClearOverride();
      ApiEndpointResolver.ClearApiKeyOverride();
    }

    [TearDown]
    public void TearDown()
    {
      ApiEndpointResolver.ClearOverride();
      ApiEndpointResolver.ClearApiKeyOverride();
    }

    [Test]
    public void Resolve_UsesNormalizedFallback_WhenNoOverridesExist()
    {
      var resolved = ApiEndpointResolver.Resolve("https://api.example.com/");
      Assert.AreEqual("https://api.example.com", resolved);
    }

    [Test]
    public void Resolve_UsesPlayerPrefsOverride_WhenPresent()
    {
      ApiEndpointResolver.SetOverride("http://10.0.0.2:8000/");

      var resolved = ApiEndpointResolver.Resolve("https://fallback.local/");

      Assert.AreEqual("http://10.0.0.2:8000", resolved);
      Assert.AreEqual("http://10.0.0.2:8000", PlayerPrefs.GetString(ApiEndpointResolver.PlayerPrefsKey));
    }

    [Test]
    public void ResolveApiKey_UsesPlayerPrefsOverride_AndFallsBackAfterClear()
    {
      ApiEndpointResolver.SetApiKeyOverride("  test-key  ");
      Assert.AreEqual("test-key", ApiEndpointResolver.ResolveApiKey("fallback-key"));

      ApiEndpointResolver.ClearApiKeyOverride();
      Assert.AreEqual("fallback-key", ApiEndpointResolver.ResolveApiKey("fallback-key"));
    }
  }
}
