import React, { useState } from 'react';
import {
  ShieldCheck,
  Plus,
  Edit2,
  Trash2,
  RefreshCw,
  AlertCircle,
  X,
  Loader2,
  Percent,
  Tag
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import {
  useCustomerTiersQuery,
  useCreateCustomerTierMutation,
  useUpdateCustomerTierMutation,
  useDeleteCustomerTierMutation
} from '../../hooks/useBackendData';
import {
  CustomerTierResponse,
  CustomerTierCreateRequest,
  CustomerTierUpdateRequest
} from '../../types';

export const CustomerTierManagementPanel: React.FC = () => {
  const { showNotification } = useApp();

  // Queries & Mutations
  const {
    data: tiers = [],
    isLoading,
    isError,
    error,
    refetch,
    isFetching
  } = useCustomerTiersQuery();

  const createMutation = useCreateCustomerTierMutation();
  const updateMutation = useUpdateCustomerTierMutation();
  const deleteMutation = useDeleteCustomerTierMutation();

  // Modal States
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [editingTier, setEditingTier] = useState<CustomerTierResponse | null>(null);

  // Form States
  const [formName, setFormName] = useState<string>('');
  const [formDiscountLimit, setFormDiscountLimit] = useState<number>(10);
  const [formDescription, setFormDescription] = useState<string>('');
  const [formIsActive, setFormIsActive] = useState<boolean>(true);
  const [formError, setFormError] = useState<string | null>(null);

  const resetForm = () => {
    setFormName('');
    setFormDiscountLimit(10);
    setFormDescription('');
    setFormIsActive(true);
    setFormError(null);
  };

  const openAddModal = () => {
    resetForm();
    setIsAddModalOpen(true);
  };

  const openEditModal = (tier: CustomerTierResponse) => {
    setEditingTier(tier);
    setFormName(tier.name);
    setFormDiscountLimit(Number(tier.default_discount_limit) || 0);
    setFormDescription(tier.description || '');
    setFormIsActive(tier.is_active);
    setFormError(null);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) {
      setFormError('Tier Name is required.');
      return;
    }

    try {
      const payload: CustomerTierCreateRequest = {
        name: formName.trim(),
        default_discount_limit: Number(formDiscountLimit),
        description: formDescription.trim() || null,
        is_active: formIsActive
      };

      await createMutation.mutateAsync(payload);
      showNotification(`Customer tier "${payload.name}" created successfully.`, 'success');
      setIsAddModalOpen(false);
      resetForm();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create customer tier.';
      setFormError(msg);
    }
  };

  const handleUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTier) return;
    if (!formName.trim()) {
      setFormError('Tier Name is required.');
      return;
    }

    try {
      const payload: CustomerTierUpdateRequest = {
        name: formName.trim(),
        default_discount_limit: Number(formDiscountLimit),
        description: formDescription.trim() || null,
        is_active: formIsActive
      };

      await updateMutation.mutateAsync({ id: editingTier.id, payload });
      showNotification(`Customer tier "${payload.name}" updated successfully.`, 'success');
      setEditingTier(null);
      resetForm();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update customer tier.';
      setFormError(msg);
    }
  };

  const handleDeactivate = async (tier: CustomerTierResponse) => {
    const confirmAction = window.confirm(
      `Are you sure you want to deactivate customer tier "${tier.name}"? Active customers on this tier may be affected.`
    );
    if (!confirmAction) return;

    try {
      await deleteMutation.mutateAsync(tier.id);
      showNotification(`Customer tier "${tier.name}" deactivated successfully.`, 'success');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to deactivate customer tier.';
      showNotification(msg, 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-amber-600" />
            <h3 className="text-sm font-bold text-slate-900">Customer Tier Governance</h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Configure authoritative tier discount limits, policy ceilings, and commercial descriptions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1 px-3 py-2 text-xs font-semibold rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition cursor-pointer disabled:opacity-50"
            title="Refresh Tiers"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={openAddModal}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Customer Tier</span>
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {isError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error instanceof Error ? error.message : 'Error loading customer tiers from backend.'}</span>
        </div>
      )}

      {/* Tiers Grid / Cards Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {tiers.map((tier) => (
          <div
            key={tier.id}
            className={`rounded-xl border p-4 shadow-xs flex flex-col justify-between transition ${
              tier.is_active
                ? 'bg-white border-slate-200 hover:border-slate-300'
                : 'bg-slate-50 border-slate-200 opacity-60'
            }`}
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                  {tier.name}
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                    tier.is_active
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-slate-100 text-slate-500 border-slate-200'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${tier.is_active ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
                  {tier.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="mt-3 space-y-1.5 text-xs text-slate-600">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1 text-slate-500">
                    <Percent className="w-3 h-3 text-blue-600" /> Discount Limit:
                  </span>
                  <span className="font-mono font-bold text-blue-600">{Number(tier.default_discount_limit)}%</span>
                </div>
              </div>

              {tier.description && (
                <div className="mt-3 pt-2.5 border-t border-slate-100 text-[11px] text-slate-500 line-clamp-2">
                  <span className="font-semibold text-slate-700">Description: </span>
                  {tier.description}
                </div>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
              <button
                onClick={() => openEditModal(tier)}
                className="px-2.5 py-1.5 rounded text-xs font-semibold text-slate-600 hover:text-blue-600 hover:bg-blue-50 transition cursor-pointer flex items-center gap-1"
                title="Edit Tier"
              >
                <Edit2 className="w-3 h-3" />
                <span>Edit</span>
              </button>
              {tier.is_active && (
                <button
                  onClick={() => handleDeactivate(tier)}
                  className="px-2.5 py-1.5 rounded text-xs font-semibold text-rose-600 hover:bg-rose-50 transition cursor-pointer flex items-center gap-1"
                  title="Deactivate Tier"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Deactivate</span>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Main Table Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900">All Configured Customer Tiers</h3>
          <span className="text-xs text-slate-500 font-mono">
            {tiers.length} Tiers Configured
          </span>
        </div>

        {isLoading && tiers.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            <span>Loading customer tiers from backend...</span>
          </div>
        ) : tiers.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No customer tiers configured. Click "Add Customer Tier" to register one.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                  <th className="py-3 px-4">Tier Name</th>
                  <th className="py-3 px-3">Default Discount Limit</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Created</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tiers.map((tier) => (
                  <tr key={tier.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 px-4 font-bold text-slate-900">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200 text-[11px] font-mono">
                        {tier.name}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono font-bold text-blue-600">
                        {Number(tier.default_discount_limit)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600 text-[11px] max-w-xs truncate">
                      {tier.description || '—'}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          tier.is_active
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-slate-100 text-slate-500 border-slate-200'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${tier.is_active ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
                        {tier.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {tier.created_at ? new Date(tier.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openEditModal(tier)}
                          className="px-2.5 py-1 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded transition cursor-pointer font-semibold text-xs flex items-center gap-1"
                        >
                          <Edit2 className="w-3 h-3" />
                          <span>Edit</span>
                        </button>
                        {tier.is_active && (
                          <button
                            onClick={() => handleDeactivate(tier)}
                            className="px-2.5 py-1 text-rose-600 hover:bg-rose-50 rounded transition cursor-pointer font-semibold text-xs flex items-center gap-1"
                          >
                            <Trash2 className="w-3 h-3" />
                            <span>Deactivate</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Create Customer Tier</h3>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-5 space-y-4 text-xs">
              {formError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{formError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1">
                  Tier Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. PLATINUM, GOLD, SILVER"
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1">
                  Default Discount Limit (%) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={formDiscountLimit}
                  onChange={(e) => setFormDiscountLimit(parseFloat(e.target.value) || 0)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1">
                  Description / Commercial Rules
                </label>
                <textarea
                  rows={2}
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="e.g. Premium enterprise account tier with accelerated fulfillment"
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition resize-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="createTierActiveCheckbox"
                  checked={formIsActive}
                  onChange={(e) => setFormIsActive(e.target.checked)}
                  className="w-4 h-4 rounded text-blue-600 accent-blue-600 focus:ring-blue-500 border-slate-300 cursor-pointer"
                />
                <label htmlFor="createTierActiveCheckbox" className="text-xs font-medium text-slate-700 cursor-pointer select-none">
                  Active tier status (default enabled)
                </label>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-3.5 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
                >
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Creating...</span>
                    </>
                  ) : (
                    <span>Create Tier</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingTier && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Edit Customer Tier: {editingTier.name}</h3>
              </div>
              <button
                onClick={() => setEditingTier(null)}
                className="text-slate-400 hover:text-slate-600 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUpdateSubmit} className="p-5 space-y-4 text-xs">
              {formError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{formError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1">
                  Tier Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1">
                  Default Discount Limit (%) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={formDiscountLimit}
                  onChange={(e) => setFormDiscountLimit(parseFloat(e.target.value) || 0)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1">
                  Description / Commercial Rules
                </label>
                <textarea
                  rows={2}
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition resize-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="editTierActiveCheckbox"
                  checked={formIsActive}
                  onChange={(e) => setFormIsActive(e.target.checked)}
                  className="w-4 h-4 rounded text-blue-600 accent-blue-600 focus:ring-blue-500 border-slate-300 cursor-pointer"
                />
                <label htmlFor="editTierActiveCheckbox" className="text-xs font-medium text-slate-700 cursor-pointer select-none">
                  Active tier status
                </label>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingTier(null)}
                  className="px-3.5 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
                >
                  {updateMutation.isPending ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <span>Save Changes</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
