
import { useQuery } from '@tanstack/react-query';
import { getBots } from '@/lib/mockData';

export const useBots = () => {
  return useQuery({
    queryKey: ['bots'],
    queryFn: getBots,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
