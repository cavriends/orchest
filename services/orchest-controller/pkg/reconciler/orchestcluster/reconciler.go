package orchestcluster

import (
	"context"

	orchestv1alpha1 "github.com/orchest/orchest/services/orchest-controller/pkg/apis/orchest/v1alpha1"
	"github.com/orchest/orchest/services/orchest-controller/pkg/utils"
	"github.com/pkg/errors"
	kerrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/klog/v2"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	k8smanager "sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

// OrchestClusterReconciler reconciles OrchestCluster CRD.
type OrchestClusterReconciler struct {
	client client.Client
	scheme *runtime.Scheme
}

// NewOrchestClusterReconciler returns a new *OrchestClusterReconciler.
func NewOrchestClusterReconciler(mgr k8smanager.Manager) *OrchestClusterReconciler {

	reconciler := OrchestClusterReconciler{
		client: mgr.GetClient(),
		scheme: mgr.GetScheme(),
	}

	return &reconciler
}

func (r *OrchestClusterReconciler) Reconcile(ctx context.Context, req ctrl.Request) (_ ctrl.Result, reterr error) {

	// Get OrchestCluster CRD from kubernetes
	cluster := &orchestv1alpha1.OrchestCluster{}
	err := r.client.Get(ctx, req.NamespacedName, cluster)
	if err != nil {
		if kerrors.IsNotFound(err) {
			klog.V(2).Info("OrchestCluster %s resource not found.", req.NamespacedName)
			return reconcile.Result{}, nil
		}
		// Error reading OrchestCluster - The request will be requeued.
		return reconcile.Result{}, errors.Wrap(err, "failed to get OrchestCluster")
	}

	// Set a finalizer so we can do cleanup before the object goes away
	err = utils.AddFinalizerIfNotPresent(ctx, r.client, cluster, orchestv1alpha1.Finalizer)
	if err != nil {
		return reconcile.Result{}, errors.Wrap(err, "failed to add finalizer")
	}

	if !cluster.GetDeletionTimestamp().IsZero() {
		// The cluster is deleted, delete it
		return r.deleteOrchestCluster(ctx, req)
	}

	// Reconciling
	// TODO

	// Return and do not requeue
	return reconcile.Result{}, nil
}

func (r *OrchestClusterReconciler) deleteOrchestCluster(ctx context.Context,
	req ctrl.Request) (reconcile.Result, error) {

	cluster := &orchestv1alpha1.OrchestCluster{}
	if err := r.client.Get(ctx, req.NamespacedName, cluster); err != nil {
		return reconcile.Result{}, errors.Wrapf(err, "failed to get cluster %v during deleting cluster.", req.NamespacedName)
	}

	// Update Cluster status
	r.updateClusterStatus(ctx, cluster, orchestv1alpha1.StateDeleting, "Deleting the Cluster")

	// Remove finalizers
	err := utils.RemoveFinalizerIfNotPresent(ctx, r.client, cluster, orchestv1alpha1.Finalizer)
	if err != nil {
		return reconcile.Result{}, errors.Wrap(err, "failed to remove finalizers")
	}

	return reconcile.Result{}, nil
}

func (r *OrchestClusterReconciler) updateClusterStatus(ctx context.Context, cluster *orchestv1alpha1.OrchestCluster,
	state orchestv1alpha1.OrchestClusterState, message string) error {

	cluster.Status = orchestv1alpha1.OrchestClusterStatus{
		State:   state,
		Message: message,
	}

	return r.client.Status().Update(ctx, cluster)

}
