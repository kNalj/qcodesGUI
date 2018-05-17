from random import randint
import time
import datetime


random = {1: "If you try to fail, and succeed, which have you done? ",
          2: "People say nothing is impossible, but I do nothing every day.",
          3: "Never put off until tomorrow what you can do the day after tomorrow.",
          4: "Follow your passion, stay true to yourself, never follow someone else’s path unless you’re in the woods "
             "and you’re lost and you see a path then by all means you should follow that.",
          5: "I have not failed. I’ve just found 10,000 ways that don’t work.",
          6: "By working faithfully eight hours a day you may eventually get to be boss and work twelve hours a day. ",
          7: "My therapist told me the way to achieve true inner peace is to finish what I start. So far I’ve finished "
             "two bags of M&Ms and a chocolate cake. I feel better already.",
          8: "I always give 100% at Work: 10% Monday, 23% Tuesday, 40% Wednesday, 22% Thursday, and 5% Friday.",
          9: "Hard work never killed anybody, but why take a chance? ",
          10: "I don’t mind coming to work, but this eight hour wait to go home is just bullshit!",
          11: "Fish who are caught and released are like the aquatic equivalent of people who claim to have been "
              "abducted by aliens.",
          12: "Most of my clothes have been to countries that I have not.",
          13: "I have no idea what I've forgotten.",
          14: "The person who would proof read Hitler's speeches was a grammar Nazi.",
          15: ""}
while True:
    print(random[randint(1, len(random))])
    time.sleep(2)
