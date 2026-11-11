Name:		junixsocket-common
Version:	2.8.3
Release:	1
Summary:	Java API for Unix domain sockets
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/kohlschutter/junixsocket
# Tag junixsocket-2.8.3. The two prebuilt jars in that tag are removed
# before this archive is stored.
Source0:	https://github.com/kohlschutter/junixsocket/archive/refs/tags/junixsocket-%{version}.tar.gz#/junixsocket-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(com.google.errorprone:error_prone_annotations)

%description
junixsocket-common is the pure Java API for AF_UNIX sockets.
mwiede jsch 0.2.16, pinned by Gradle 9.9.1, compiles against
AFUNIXSocketAddress, AFUNIXSocketChannel, and AFUNIXServerSocketChannel.
The native library is a separate artifact and is not in this package.
Class files in the root of the jar are Java 8. SocketAddressUtil for
UnixDomainSocketAddress is the Java 16 copy under META-INF/versions/16.

%prep
%autosetup -n junixsocket-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
BP=junixsocket-common/src/main/java-unresolved-properties/org/newsclub/net/unix/BuildProperties.java
sed -i \
	-e 's|${project.version}|%{version}|g' \
	-e 's|${git.build.version}|%{version}|g' \
	-e 's|${git.commit.id.abbrev}|%{version}|g' \
	-e 's|${git.commit.id.full}|junixsocket-%{version}|g' \
	-e 's|${git.commit.time}|2023-12-01T00:00:00Z|g' \
	-e 's|${git.dirty}|false|g' \
	"$BP"
if grep -F '${' "$BP"; then
	echo "BuildProperties still has unresolved tokens" >&2
	exit 1
fi

mkdir -p ann-src/com/kohlschutter/annotations/compiletime
mkdir -p ann-src/org/codehaus/mojo/animal_sniffer
mkdir -p ann-src/org/eclipse/jdt/annotation
cat > ann-src/org/eclipse/jdt/annotation/NonNull.java << 'END'
package org.eclipse.jdt.annotation;
import java.lang.annotation.*;
@Retention(RetentionPolicy.CLASS)
@Target({ElementType.TYPE,ElementType.FIELD,ElementType.METHOD,ElementType.PARAMETER,ElementType.LOCAL_VARIABLE,ElementType.TYPE_USE,ElementType.TYPE_PARAMETER})
public @interface NonNull {}
END
cat > ann-src/org/eclipse/jdt/annotation/Nullable.java << 'END'
package org.eclipse.jdt.annotation;
import java.lang.annotation.*;
@Retention(RetentionPolicy.CLASS)
@Target({ElementType.TYPE,ElementType.FIELD,ElementType.METHOD,ElementType.PARAMETER,ElementType.LOCAL_VARIABLE,ElementType.TYPE_USE,ElementType.TYPE_PARAMETER})
public @interface Nullable {}
END
cat > ann-src/org/eclipse/jdt/annotation/NonNullByDefault.java << 'END'
package org.eclipse.jdt.annotation;
import java.lang.annotation.*;
@Retention(RetentionPolicy.CLASS)
@Target({ElementType.PACKAGE,ElementType.TYPE,ElementType.METHOD,ElementType.CONSTRUCTOR,ElementType.FIELD,ElementType.LOCAL_VARIABLE})
public @interface NonNullByDefault {}
END
cat > ann-src/com/kohlschutter/annotations/compiletime/SuppressFBWarnings.java << 'END'
package com.kohlschutter.annotations.compiletime;
import java.lang.annotation.*;
@Retention(RetentionPolicy.CLASS)
@Target({ElementType.TYPE,ElementType.FIELD,ElementType.METHOD,ElementType.CONSTRUCTOR,ElementType.PARAMETER,ElementType.LOCAL_VARIABLE})
public @interface SuppressFBWarnings {
	String[] value() default {};
	String justification() default "";
}
END
cat > ann-src/com/kohlschutter/annotations/compiletime/ExcludeFromCodeCoverageGeneratedReport.java << 'END'
package com.kohlschutter.annotations.compiletime;
import java.lang.annotation.*;
@Retention(RetentionPolicy.CLASS)
@Target({ElementType.TYPE,ElementType.METHOD,ElementType.CONSTRUCTOR})
public @interface ExcludeFromCodeCoverageGeneratedReport {
	String reason() default "";
}
END
cat > ann-src/org/codehaus/mojo/animal_sniffer/IgnoreJRERequirement.java << 'END'
package org.codehaus.mojo.animal_sniffer;
import java.lang.annotation.*;
@Retention(RetentionPolicy.CLASS)
@Target({ElementType.METHOD,ElementType.CONSTRUCTOR,ElementType.TYPE})
public @interface IgnoreJRERequirement {}
END
mkdir -p ann-classes
javac --release 8 -encoding UTF-8 -d ann-classes $(find ann-src -name '*.java')

find junixsocket-common/src/main/java8 -name '*.java' > sources.list
find junixsocket-common/src/main/java -name '*.java' \
	! -name module-info.java \
	! -name SocketAddressUtil.java \
	! -name AFInputStream.java \
	! -name AFOutputStream.java \
	! -name CleanableState.java \
	! -name DatagramSocketImplShim.java \
	! -name DatagramSocketShim.java \
	! -name PathUtil.java \
	! -name SocketImplShim.java \
	>> sources.list
printf '%s\n' \
	junixsocket-common/src/main/java15/org/newsclub/net/unix/SocketAddressUtil.java \
	junixsocket-common/src/main/java-unresolved-properties/org/newsclub/net/unix/BuildProperties.java \
	>> sources.list
test "$(wc -l < sources.list)" -eq 93

mkdir -p classes
javac --release 8 -encoding UTF-8 \
	-cp "ann-classes:%{_javadir}/error_prone_annotations.jar" \
	-d classes @sources.list
/bin/cp -a junixsocket-common/src/main/resources/. classes/
mkdir -p classes/META-INF/versions/16
javac --release 16 -encoding UTF-8 \
	-cp "ann-classes:%{_javadir}/error_prone_annotations.jar:classes" \
	-d classes/META-INF/versions/16 \
	junixsocket-common/src/main/java/org/newsclub/net/unix/SocketAddressUtil.java

cat > manifest.txt << 'END'
Manifest-Version: 1.0
Multi-Release: true
END
jar cfm junixsocket-common.jar manifest.txt -C classes .
jar tf junixsocket-common.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
jar tf junixsocket-common.jar | grep -q 'org/eclipse/jdt/annotation/NonNull.class' && exit 1 || true
javap -v -classpath junixsocket-common.jar org.newsclub.net.unix.AFUNIXSocketAddress | grep -q 'major version: 52'
javap -v -classpath junixsocket-common.jar org.newsclub.net.unix.AFUNIXSocketChannel | grep -q 'major version: 52'
javap -v -classpath junixsocket-common.jar org.newsclub.net.unix.AFUNIXServerSocketChannel | grep -q 'major version: 52'

cat > junixsocket-common.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.kohlschutter.junixsocket</groupId>
  <artifactId>junixsocket-common</artifactId>
  <version>2.8.3</version>
  <name>junixsocket-common</name>
  <description>Java API for Unix domain sockets</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact junixsocket-common.pom:junixsocket-common.jar \
	--file-name junixsocket-common \
	--filelist .mfiles

%check
mkdir -p check
cat > check/Smoke.java << 'END'
import java.io.File;
import org.newsclub.net.unix.AFUNIXServerSocketChannel;
import org.newsclub.net.unix.AFUNIXSocketAddress;
import org.newsclub.net.unix.AFUNIXSocketChannel;
public class Smoke {
	public static void main(String[] args) throws Exception {
		AFUNIXSocketAddress address = AFUNIXSocketAddress.of(new File("/junix-check.sock"));
		System.out.println("junix_ok " + address.getPath()
			+ " " + AFUNIXSocketChannel.class.getSimpleName()
			+ " " + AFUNIXServerSocketChannel.class.getSimpleName());
	}
}
END
JAR=%{buildroot}%{_javadir}/junixsocket-common.jar
test -f "$JAR"
javac --release 8 -encoding UTF-8 -cp "$JAR" -d check check/Smoke.java
java -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'junix_ok /junix-check.sock AFUNIXSocketChannel AFUNIXServerSocketChannel' check/out.txt

%files -f .mfiles
%doc LICENSE NOTICE
