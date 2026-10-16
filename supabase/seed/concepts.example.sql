-- Illustrative, non-production learning content. No users or learner records.
BEGIN;
INSERT INTO public.concepts(name,definition,acceptable_extensions,dict_content,category)
VALUES
 ('inflation','A sustained increase in the general price level.','Distinguish general inflation from a change in one relative price.','A sustained increase in the general price level reduces the purchasing power of money.','academic'),
 ('opportunity cost','The value of the best alternative forgone when making a choice.','Includes non-monetary alternatives.','Choosing one alternative means giving up the next best alternative.','academic'),
 ('exchange rate','The price of one currency expressed in terms of another currency.','State the quotation convention when describing an increase.','An exchange rate expresses the value of one currency relative to another.','market'),
 ('base interest rate','A policy interest rate set or targeted by a central bank.','Transmission to other rates can vary by market conditions.','A central bank policy rate influences borrowing costs and monetary conditions.','macro')
ON CONFLICT(name) DO NOTHING;
INSERT INTO public.questions(concept_id,question_text,option_1,option_2,option_3,option_4,option_5,correct_option,commentary)
SELECT concept_id,'Which description best defines inflation?',
 'A sustained increase in the general price level','A fall in one product price','Any increase in real output',
 'A permanent increase in purchasing power','An exchange rate quotation',1,
 'Inflation concerns the general price level over time, not an isolated relative-price change.'
FROM public.concepts c WHERE c.name='inflation'
AND NOT EXISTS (SELECT 1 FROM public.questions q WHERE q.concept_id=c.concept_id
 AND q.question_text='Which description best defines inflation?');
COMMIT;
