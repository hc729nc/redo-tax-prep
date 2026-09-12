import { create } from "zustand";
import type { TaxReturn } from "../api/returnsApi";

interface ReturnStore {
  activeReturn: TaxReturn | null;
  setActiveReturn: (r: TaxReturn | null) => void;
}

export const useReturnStore = create<ReturnStore>((set) => ({
  activeReturn: null,
  setActiveReturn: (r) => set({ activeReturn: r }),
}));
