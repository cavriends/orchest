package addons

import (
	"context"
	"path"

	orchestv1alpha1 "github.com/orchest/orchest/services/orchest-controller/pkg/apis/orchest/v1alpha1"
	"github.com/orchest/orchest/services/orchest-controller/pkg/utils"
	"k8s.io/klog/v2"
)

var (
	// list of all addons
	ArgoWorkflow   = "argo-workflow"
	DockerRegistry = "docker-regitry"
)

type AddonsConfig struct {

	// The list of addons to disable
	DisabledAddons []string

	AssetDir string

	DefaultNamespace string
}

func NewDefaultAddonsConfig() AddonsConfig {
	return AddonsConfig{
		DisabledAddons: []string{ArgoWorkflow},

		AssetDir: "deploy",

		DefaultNamespace: "orchest",
	}
}

type Addon interface {
	// Installs addon if the config is changed
	Enable(ctx context.Context, namespace string, orchest *orchestv1alpha1.OrchestCluster) error

	// Uninstall the addon
	Uninstall(ctx context.Context, namespace string) error
}

// AddonManager holds the map of deployers
type AddonManager struct {
	config AddonsConfig
	addons map[string]Addon
}

func NewAddonManager(config AddonsConfig) *AddonManager {

	addonManager := AddonManager{
		config: config,
		addons: make(map[string]Addon),
	}

	addonManager.AddAddon("argo",
		NewHelmDeployer("argo",
			path.Join(config.AssetDir, "thirdparty/argo-workflows"),
			path.Join(config.AssetDir, "thirdparty/argo-workflows/orchest-values.yaml")))

	addonManager.AddAddon("registry",
		NewHelmDeployer("registry",
			path.Join(config.AssetDir, "thirdparty/docker-registry/helm"),
			path.Join(config.AssetDir, "thirdparty/docker-registry/orchest-values.yaml")))

	return &addonManager
}

// Run will not return until stopCh is closed. workers determines how many
// objects will be handled in parallel.
func (m *AddonManager) Run(stopCh <-chan struct{}) {

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	for addonName, addon := range m.addons {

		//addon is not disabled
		if !utils.Contains(m.config.DisabledAddons, addonName) {

			err := addon.Enable(ctx, m.config.DefaultNamespace, nil)

			if err != nil {
				klog.Errorf("failed to deploy addon: %s, err: %s", addonName, err)
			} else {
				klog.Infof("addon is enabled %s", addonName)
				defer addon.Uninstall(ctx, m.config.DefaultNamespace)
			}
		}
	}

	for _, addonName := range m.config.DisabledAddons {
		if addon, ok := m.addons[addonName]; ok {
			// enable addon
			addon.Enable(ctx, m.config.DefaultNamespace, nil)
			defer addon.Uninstall(ctx, m.config.DefaultNamespace)
		} else {
			klog.Warningf("Addon %s is not registered with addon manager")
		}
	}

	<-stopCh

}

// add an addon, if not already registred with the manager
func (m *AddonManager) AddAddon(name string, addon Addon) {

	// If already registred, log warning and return
	if _, ok := m.addons[name]; ok {
		klog.Warningf("addon %s is already registred with addon manager", name)
	}

	m.addons[name] = addon
	klog.V(2).Info("addon is registred with addon manager")
}

// get a deployer by the name
func (m *AddonManager) Get(name string) Addon {
	return m.addons[name]
}