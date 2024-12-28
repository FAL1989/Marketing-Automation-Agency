import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const formatDate = (date: string | Date) => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return format(dateObj, "d 'de' MMMM 'às' HH:mm", { locale: ptBR });
}; 