

class TWUpdateRule(object):

	class builtin_update_rules():
		
		def step_by_step_ls(oldvalue,feedback,learningspeed,recipient):
			"""
			The return value is simply a function of the old one, the received
			feedback (that is a 'this should be the answer' indication) and 
			the learning speed.
			"""
			return oldvalue - (oldvalue - feedback.value) * learningspeed
			
		def average_of_all_fbs(oldvalue,feedback,learningspeed,recipient):
			"""
			A more stable feedback calculator: the trustworthiness for a given
			ctype is in this case an average of all feedback ever received
			about that pair.
			"""
			
			allfeedback = recipient.received_feedback[fb.about]
			
			allvalues = tuple(fb.value for fb in allfeedback)
			
			return sum(allvalues) / len(allvalues)

		def average_of_most_recent_fbs(oldvalue,feedback,learningspeed,recipient,crop = 10):
			
			allfeedback = recipient.received_feedback[fb.about]
			
			if crop > len(allfeedback):
				topmost_crop = allfeedback[len(feedback) - crop: ]
			
			else:
				topmost_crop = allfeedback
			
			allvalues = tuple(fb.value for fb in topmost_crop)
			
			return sum(allvalues) / len(allvalues)

		def median_of_all_fbs(oldvalue,feedback,learningspeed,recipient):
			"""
			Even more stable: takes the median of all feedback ever received
			about that pair.
			"""
			
			allfeedback = recipient.received_feedback[fb.about]
			
			allvalues = tuple(fb.value for fb in allfeedback)
			
			sorts = sorted(allvalues)
			
			if len(sorts) % 2 != 0:
				center = sorts[len((sorts-1) // 2) ] # the middle value
			else:
				centers = sorts[(len(sorts) // 2) -1 : (len(sorts) // 2) +1]
				center = sum(centers) / 2
				
			return center
		
		def median_of_most_recent_fbs(oldvalue,feedback,learningspeed,recipient,crop = 10):
			
			allfeedback = recipient.received_feedback[fb.about]
			
			if crop > len(allfeedback):
				topmost_crop = allfeedback[len(feedback) - crop: ]
			
			else:
				topmost_crop = allfeedback			
				
			allvalues = tuple(fb.value for fb in topmost_crop)
			
			sorts = sorted(allvalues)
			
			if len(sorts) % 2 != 0:
				center = sorts[len((sorts-1) // 2) ] # the middle value
			else:
				centers = sorts[(len(sorts) // 2) -1 : (len(sorts) // 2) +1]
				center = sum(centers) / 2
				
			return center			
