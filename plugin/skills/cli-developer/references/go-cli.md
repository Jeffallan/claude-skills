# Go CLI Development

## Cobra (Recommended)

Powerful CLI framework used by kubectl, hugo, docker.

```go
// cmd/root.go
package cmd

import (
    "fmt"
    "os"
    "github.com/spf13/cobra"
    "github.com/spf13/viper"
)

var (
    cfgFile string
    verbose bool
)

var rootCmd = &cobra.Command{
    Use:   "mycli",
    Short: "My awesome CLI tool",
    Long: `A longer description of your CLI application`,
    Version: "1.0.0",
}

func Execute() {
    if err := rootCmd.Execute(); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}

func init() {
    cobra.OnInitialize(initConfig)

    rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file")
    rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "verbose output")

    viper.BindPFlag("verbose", rootCmd.PersistentFlags().Lookup("verbose"))
}

func initConfig() {
    if cfgFile != "" {
        viper.SetConfigFile(cfgFile)
    } else {
        home, err := os.UserHomeDir()
        cobra.CheckErr(err)

        viper.AddConfigPath(home)
        viper.AddConfigPath(".")
        viper.SetConfigType("yaml")
        viper.SetConfigName(".mycli")
    }

    viper.AutomaticEnv()

    if err := viper.ReadInConfig(); err == nil {
        fmt.Fprintln(os.Stderr, "Using config file:", viper.ConfigFileUsed())
    }
}

// cmd/init.go
package cmd

import (
    "fmt"
    "github.com/spf13/cobra"
)

var (
    template string
    force    bool
)

var initCmd = &cobra.Command{
    Use:   "init [name]",
    Short: "Initialize a new project",
    Args:  cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        name := args[0]
        return initProject(name, template, force)
    },
}

func init() {
    rootCmd.AddCommand(initCmd)

    initCmd.Flags().StringVarP(&template, "template", "t", "default", "Project template")
    initCmd.Flags().BoolVarP(&force, "force", "f", false, "Overwrite existing")
}

func initProject(name, template string, force bool) error {
    fmt.Printf("Creating %s from %s\n", name, template)
    return nil
}

// cmd/deploy.go
package cmd

import (
    "fmt"
    "github.com/spf13/cobra"
)

var (
    dryRun bool
)

var deployCmd = &cobra.Command{
    Use:   "deploy [environment]",
    Short: "Deploy to environment",
    Args:  cobra.ExactArgs(1),
    ValidArgs: []string{"dev", "staging", "prod"},
    RunE: func(cmd *cobra.Command, args []string) error {
        env := args[0]
        return deploy(env, dryRun)
    },
}

func init() {
    rootCmd.AddCommand(deployCmd)
    deployCmd.Flags().BoolVar(&dryRun, "dry-run", false, "Preview only")
}

func deploy(env string, dryRun bool) error {
    if dryRun {
        fmt.Printf("Would deploy to: %s\n", env)
    } else {
        fmt.Printf("Deploying to %s...\n", env)
    }
    return nil
}

// main.go
package main

import "mycli/cmd"

func main() {
    cmd.Execute()
}
```

## Viper (Configuration)

Configuration management with multiple sources.

```go
package config

import (
    "fmt"
    "github.com/spf13/viper"
)

type Config struct {
    Environment string `mapstructure:"environment"`
    Timeout     int    `mapstructure:"timeout"`
    Verbose     bool   `mapstructure:"verbose"`
    API         APIConfig `mapstructure:"api"`
}

type APIConfig struct {
    Endpoint string `mapstructure:"endpoint"`
    Token    string `mapstructure:"token"`
}

func Load() (*Config, error) {
    // Set defaults
    viper.SetDefault("environment", "development")
    viper.SetDefault("timeout", 30)
    viper.SetDefault("verbose", false)

    // Config file locations
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath("/etc/mycli/")
    viper.AddConfigPath("$HOME/.config/mycli")
    viper.AddConfigPath(".")

    // Environment variables
    viper.SetEnvPrefix("MYCLI")
    viper.AutomaticEnv()

    // Read config
    if err := viper.ReadInConfig(); err != nil {
        if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
            return nil, fmt.Errorf("failed to read config: %w", err)
        }
    }

    // Unmarshal into struct
    var cfg Config
    if err := viper.Unmarshal(&cfg); err != nil {
        return nil, fmt.Errorf("failed to unmarshal config: %w", err)
    }

    return &cfg, nil
}
```

## Bubble Tea (Interactive TUI)

Modern terminal UI framework for interactive CLIs.

```go
package main

import (
    "fmt"
    "os"

    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/lipgloss"
)

// Model
type model struct {
    choices  []string
    cursor   int
    selected map[int]struct{}
}

func initialModel() model {
    return model{
        choices:  []string{"TypeScript", "ESLint", "Prettier", "Jest"},
        selected: make(map[int]struct{}),
    }
}

// Init
func (m model) Init() tea.Cmd {
    return nil
}

// Update
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.String() {
        case "ctrl+c", "q":
            return m, tea.Quit

        case "up", "k":
            if m.cursor > 0 {
                m.cursor--
            }

        case "down", "j":
            if m.cursor < len(m.choices)-1 {
                m.cursor++
            }

        case " ":
            _, ok := m.selected[m.cursor]
            if ok {
                delete(m.selected, m.cursor)
            } else {
                m.selected[m.cursor] = struct{}{}
            }

        case "enter":
            return m, tea.Quit
        }
    }

    return m, nil
}

// View
func (m model) View() string {
    s := "Select features:\n\n"

    for i, choice := range m.choices {
        cursor := " "
        if m.cursor == i {
            cursor = ">"
        }

        checked := " "
        if _, ok := m.selected[i]; ok {
            checked = "x"
        }

        s += fmt.Sprintf("%s [%s] %s\n", cursor, checked, choice)
    }

    s += "\nPress space to select, enter to confirm, q to quit.\n"

    return s
}

func main() {
    p := tea.NewProgram(initialModel())
    if _, err := p.Run(); err != nil {
        fmt.Printf("Error: %v", err)
        os.Exit(1)
    }
}
```

## Progress Indicators

```go
package main

import (
    "fmt"
    "time"

    "github.com/schollz/progressbar/v3"
)

func main() {
    // Simple progress bar
    bar := progressbar.Default(100, "Downloading")
    for i := 0; i < 100; i++ {
        bar.Add(1)
        time.Sleep(40 * time.Millisecond)
    }

    // Custom progress bar
    bar = progressbar.NewOptions(100,
        progressbar.OptionEnableColorCodes(true),
        progressbar.OptionShowBytes(true),
        progressbar.OptionSetWidth(15),
        progressbar.OptionSetDescription("[cyan][1/3][reset] Downloading..."),
        progressbar.OptionSetTheme(progressbar.Theme{
            Saucer:        "[green]=[reset]",
            SaucerHead:    "[green]>[reset]",
            SaucerPadding: " ",
            BarStart:      "[",
            BarEnd:        "]",
        }),
    )

    for i := 0; i < 100; i++ {
        bar.Add(1)
        time.Sleep(40 * time.Millisecond)
    }
}
```

## Spinner

```go
package main

import (
    "fmt"
    "time"

    "github.com/briandowns/spinner"
)

func main() {
    s := spinner.New(spinner.CharSets[11], 100*time.Millisecond)
    s.Suffix = " Installing dependencies..."
    s.Start()

    time.Sleep(4 * time.Second)

    s.UpdateCharSet(spinner.CharSets[9])
    s.Suffix = " Processing..."
    time.Sleep(2 * time.Second)

    s.Stop()
    fmt.Println("✓ Done!")
}
```

## Colored Output

```go
package main

import (
    "github.com/fatih/color"
)

func main() {
    // Basic colors
    color.Blue("Info: Starting deployment...")
    color.Green("Success: Deployment complete!")
    color.Yellow("Warning: Deprecated flag used")
    color.Red("Error: Deployment failed")

    // Custom styles
    success := color.New(color.FgGreen, color.Bold).PrintlnFunc()
    error := color.New(color.FgRed, color.Bold).PrintlnFunc()

    success("✓ Build successful")
    error("✗ Build failed")

    // Printf-style
    color.Cyan("Processing %d files...\n", 42)

    // Disable colors for CI
    if os.Getenv("CI") != "" {
        color.NoColor = true
    }
}
```

## Error Handling

```go
package main

import (
    "errors"
    "fmt"
    "os"
    "syscall"

    "github.com/spf13/cobra"
)

var deployCmd = &cobra.Command{
    Use:   "deploy",
    Short: "Deploy application",
    RunE: func(cmd *cobra.Command, args []string) error {
        if err := deploy(); err != nil {
            return handleError(err)
        }
        return nil
    },
}

func handleError(err error) error {
    var exitCode int

    switch {
    case errors.Is(err, os.ErrPermission):
        fmt.Fprintln(os.Stderr, "Permission denied")
        fmt.Fprintln(os.Stderr, "Try running with sudo or check file permissions")
        exitCode = 77

    case errors.Is(err, os.ErrNotExist):
        fmt.Fprintf(os.Stderr, "File not found: %v\n", err)
        exitCode = 127

    default:
        fmt.Fprintf(os.Stderr, "Deployment failed: %v\n", err)
        if os.Getenv("DEBUG") != "" {
            fmt.Fprintf(os.Stderr, "%+v\n", err)
        }
        exitCode = 1
    }

    os.Exit(exitCode)
    return nil
}

// Handle SIGINT (Ctrl+C)
func main() {
    // Setup signal handling
    c := make(chan os.Signal, 1)
    signal.Notify(c, os.Interrupt, syscall.SIGTERM)

    go func() {
        <-c
        fmt.Println("\nOperation cancelled")
        os.Exit(130)
    }()

    cmd.Execute()
}
```

## Testing

```go
package cmd

import (
    "bytes"
    "testing"

    "github.com/spf13/cobra"
    "github.com/stretchr/testify/assert"
)

func TestInitCommand(t *testing.T) {
    cmd := &cobra.Command{Use: "test"}
    cmd.AddCommand(initCmd)

    b := bytes.NewBufferString("")
    cmd.SetOut(b)
    cmd.SetArgs([]string{"init", "my-project"})

    err := cmd.Execute()
    assert.NoError(t, err)
    assert.Contains(t, b.String(), "Creating my-project")
}

func TestInitWithTemplate(t *testing.T) {
    cmd := &cobra.Command{Use: "test"}
    cmd.AddCommand(initCmd)

    b := bytes.NewBufferString("")
    cmd.SetOut(b)
    cmd.SetArgs([]string{"init", "my-project", "--template", "react"})

    err := cmd.Execute()
    assert.NoError(t, err)
    assert.Contains(t, b.String(), "react")
}
```

## Build & Distribution

```makefile
# Makefile
VERSION := $(shell git describe --tags --always --dirty)
LDFLAGS := -ldflags "-X main.version=$(VERSION)"

.PHONY: build
build:
	go build $(LDFLAGS) -o bin/mycli main.go

.PHONY: install
install:
	go install $(LDFLAGS)

.PHONY: test
test:
	go test -v ./...

.PHONY: release
release:
	GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o bin/mycli-linux-amd64
	GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o bin/mycli-darwin-amd64
	GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o bin/mycli-darwin-arm64
	GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o bin/mycli-windows-amd64.exe
```
