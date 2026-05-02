@REM
@REM Gradle startup script for Windows
@REM

@if "%DEBUG%" == "" @echo off
@setlocal

set APP_BASE_NAME=%~n0
set DIRNAME=%~dp0

if "%DIRNAME%" == "" set DIRNAME=.
set APP_HOME=%DIRNAME%

set DEFAULT_JVM_OPTS=-Xmx64m -Xms64m

set CLASSPATH=%APP_HOME%\gradle\wrapper\gradle-wrapper.jar

if not "%JAVA_HOME%" == "" (
	set JAVACMD=%JAVA_HOME%\bin\java.exe
) else (
	set JAVACMD=java.exe
)

"%JAVACMD%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %GRADLE_OPTS% -Dorg.gradle.appname=%APP_BASE_NAME% -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*

@endlocal
