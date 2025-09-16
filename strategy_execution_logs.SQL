create view public.daily_strategy_report as

select

date (pattern_detected_at) as report_date,

strategy_name,

count(*) as patterns_found,

count(

case

when final_result::text = 'WIN'::text then 1

else null::integer

end

) as wins,

count(

case

when final_result::text = 'EMPATE'::text then 1

else null::integer

end

) as draws,

count(

case

when final_result::text = 'LOSS'::text then 1

else null::integer

end

) as losses,

case

when count(

case

when final_result is not null then 1

else null::integer

end

) = 0 then 0::numeric

else round(

count(

case

when final_result::text = 'WIN'::text then 1

else null::integer

end

)::numeric * 100.0 / count(

case

when final_result is not null then 1

else null::integer

end

)::numeric,

2

)

end as success_rate

from

strategy_execution_logs

where

status::text = 'COMPLETED'::text

group by

(date (pattern_detected_at)),

strategy_name

order by

(date (pattern_detected_at)) desc,

strategy_name;