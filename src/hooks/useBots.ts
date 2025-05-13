
import { useQuery } from '@tanstack/react-query';
import { getBots, Bot } from '@/lib/mockData';

export const useBots = () => {
  return useQuery<Bot[]>({
    queryKey: ['bots'],
    queryFn: getBots,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
