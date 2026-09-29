import { useQuery } from "@tanstack/react-query";
import { getAllergens, getConditions } from "../api/client";

const referenceOptions = {
  staleTime: 60 * 60 * 1000,
  refetchOnWindowFocus: false,
};

export function useAllergens() {
  return useQuery({
    ...referenceOptions,
    queryKey: ["allergens"],
    queryFn: ({ signal }) => getAllergens(signal),
  });
}

export function useConditions() {
  return useQuery({
    ...referenceOptions,
    queryKey: ["conditions"],
    queryFn: ({ signal }) => getConditions(signal),
  });
}
