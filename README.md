# Twitterbot @parsextoto: Finding Words Inside Other Words

This is the code for a Twitter bot that finds German words inside other German words. We made this for the Hackathon at [#clunc15](http://www.clunc.eu/).

## Sample Output
See [https://www.twitter.com/parsextoto](https://www.twitter.com/parsextoto) for sample output.

## init.py
This module reads our vocabulary from the source (we used the freely available [Germandict from Sourceforge](http://sourceforge.net/projects/germandict/?source=typ_redirect)) and writes each word into our database (parsextoto.sqlite). Morphological features of the words were analysed using [SMOR](https://code.google.com/p/cistern/wiki/SMOR).

## parsextoto.sqlite
The database contains all words, their POS tags and morphological features, and the word-substring pairs with their scores.

## score.py
This module calculates the funniness score of each word-substring pair. Factors that contribute to funniness are:
* the relation between the length of both words (longer substrings are better)
* the number of morphemes of the long word that are part of the short word
* whether the short word is just the long word minus common inflectional affixes
* whether the short word is at the start or end of the long word, or somewhere in between
* the number of phoneme boundaries that are crossed by the short word (this makes the pair more surprising because the connection is only apparent when you read/write it)

The funniness scores are saved in parsextoto.sqlite in the table Substring, as the attribute Score.

## bot.py
This module tweets semi-randomly generated sentences that take word-substring pairs as their central elements. Only pairs with a funniness score of 1 or above are taken into account.
The values of consumer_key, consumer_secret, access_token and access_token_secret are taken from a module named config.py. If you want to use our code with your own Twitter account, you need to write your own config.py with the values that you can generate at [https://apps.twitter.com/](https://apps.twitter.com/).
The sentences that are posted to Twitter are chosen based on the morphological features of the word and the substring.
A pair that has already been posted is marked with a value of Posted = 1 in the database to avoid repetitions.

## Additional thoughts
We were inspired by the Twitter bot [@spellwithout](https://twitter.com/spellwithout) by [@squidlarkin](https://twitter.com/squidlarkin), which tweets word pairs with the pattern "You can't spell [A] without [B]." We decided to use this general idea, but refine it by adding a variety of sentence patterns, and to use German words instead of English words. The advantage of German in this context is its productivity in generating compound words, which lead to some of our funniest word-substring pairs.
